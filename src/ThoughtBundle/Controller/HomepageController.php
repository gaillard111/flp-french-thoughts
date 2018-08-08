<?php

namespace ThoughtBundle\Controller;

//use Elastica\Filter\Bool;
//use Elastica\Filter\BoolFilter;
use Elastica\Filter\Nested;
use Elastica\Filter\Term;
use Elastica\Query\Filtered;
use Elastica\Query\MultiMatch;
use Elastica\Query\QueryString;
use FOS\ElasticaBundle\Elastica\Index;
use FOS\ElasticaBundle\Finder\FinderInterface;
use FOS\ElasticaBundle\Paginator\PaginatorAdapterInterface;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\Route;
use Symfony\Component\HttpFoundation\Cookie;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use ThoughtBundle\Entity\Thought;
use ThoughtBundle\Model\AuthorModel;
use ThoughtBundle\Model\ThoughtModel;

/**
 * Class HomepageController
 * @package ThoughtBundle\Controller
 */
class HomepageController extends Controller
{
    /**
     * @Route("/", methods={"GET"}, options={"sitemap" = true})
     *
     * @param Request $request
     * @return Response
     */
    public function indexAction(Request $request)
    {
        $start = microtime(true);

        $em = $this->getDoctrine()->getManager();

        $page = $request->query->getInt('page', 1);

        $alpha = $request->query->getAlpha('alpha', 1);

        $countItem = 10;

        /** @var ThoughtModel $modelThought */
        $modelThought = $this->container->get('thought.model.thought_model');

        $serviceSearch = $this->container->get('thought.service.search_service');

        $search = $serviceSearch->preSearch($request->get('search'));

        /** @var FinderInterface $authorsFinder */
        $authorsFinder = $this->container->get('fos_elastica.finder.app.author');

        /** @var FinderInterface $finder */
        $finder = $this->container->get('fos_elastica.finder.app.thought');

        $default = $request->query->get('default');

        $paginator  = $this->get('knp_paginator');

        if ($search || $default) {
            /** @var PaginatorAdapterInterface $thoughts */
            $thoughts = $modelThought->getThoughtsFromElastic($search, $finder, $authorsFinder);
        } else {

            if (!$page) {
                $page = 1;
            }

            $thoughts = $modelThought->getLastThoughts(50 * $page);
        }

        $cloud = $modelThought->getCloud($search['field'], $thoughts, $search['words']);

        $pagination = $paginator->paginate(
            $thoughts,
            $page,
            $countItem
        );

        $welcomeText = $em->getRepository('ThoughtBundle:Content')->findOneBy(array(
            'contentType' => 'welcome',
        ));

        $timeExecute = microtime(true) - $start;

        $collectiveChains = $em->getRepository('ThoughtBundle:Chain')->
        findBy([
            'isCollective'  => true
        ]);

        return $this->render('ThoughtBundle::homepage.html.twig', [
            'thoughts'    => $pagination,
            'timeExecute' => $timeExecute,
            'welcomeText' => $welcomeText,
            'cloud'       => $cloud['cloud'],
            'cloudStyle'  => $cloud['cloudStyle'],
            'filtersOpen' => $search['filter_open'],
            'colChains'   => $collectiveChains
        ]);
    }

    /**
     * @Route("/parse")
     *
     * @return Response
     */
    public function parseAction()
    {
        $parseService = $this->container->get('thought.parser.service')->testParse();

        return new Response('');
    }

    /**
     * @Route("/instruction", name="instruction")
     * @return Response
     */
    public function instructionAction()
    {
        return $this->render('@Thought/instruction.html.twig');
    }

    /**
     * @param integer $thoughtId
     * @param Request $request
     * @return JsonResponse
     *
     * @Route("/thought-likes/{thoughtId}", name="thought-like", requirements={"offerId" = "\d+"}, options={"expose"=true})
     */
    public function likeAction($thoughtId, Request $request)
    {
        $em = $this->getDoctrine()->getManager();

        $modelThought = $this->container->get('thought.model.thought_model');

        $thought = $em->getRepository('ThoughtBundle:Thought')->find($thoughtId);

        $result = 'add';

        if (!$thought) {
            return new JsonResponse(array(
                'success' => false,
                'message' => 'Quote not found',
            ));
        }

        $cookieQuotes = explode(',', $request->cookies->get('quotes'));

        if ($keyQuote = array_search($thoughtId, $cookieQuotes)) {
            $thought = $modelThought->removeLike($thought);
            unset($cookieQuotes[$keyQuote]);
            $result = 'remove';
        } else {
            $thought = $modelThought->addLike($thought);
            array_push($cookieQuotes, $thoughtId);
        }

        $response = new JsonResponse(array(
            'result' => $result,
            'count'  => $thought->getLiked(),
        ));

        $response->headers->setCookie(new Cookie('quotes', implode(',', $cookieQuotes), time() + (3600 * 48)));

        return $response;
    }
}
