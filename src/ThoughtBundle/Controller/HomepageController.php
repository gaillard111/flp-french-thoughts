<?php

namespace ThoughtBundle\Controller;

use Elastica\Filter\Nested;
use Elastica\Filter\Term;
use Elastica\Query\Filtered;
use Elastica\Query\MultiMatch;
use Elastica\Query\QueryString;
use FOS\ElasticaBundle\Elastica\Index;
use FOS\ElasticaBundle\Finder\FinderInterface;
use FOS\ElasticaBundle\Paginator\PaginatorAdapterInterface;
use Knp\Component\Pager\Pagination\PaginationInterface;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\Route;
use Symfony\Component\HttpFoundation\Cookie;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use ThoughtBundle\Entity\Banner;
use ThoughtBundle\Entity\Comment;
use ThoughtBundle\Entity\Like;
use ThoughtBundle\Entity\Thought;
use ThoughtBundle\Model\AuthorModel;
use ThoughtBundle\Model\ThoughtModel;
use ThoughtBundle\Repository\CommentRepository;

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

        /** @var Thought[]|PaginationInterface $pagination */
        $pagination = $paginator->paginate(
            $thoughts,
            $page,
            $countItem
        );
        $comments = [];
        foreach ($pagination as $thought) {
            $comments[$thought->getId()][] = $em->getRepository(Comment::class)->getLastComments($thought);

        }

        $welcomeText = $em->getRepository('ThoughtBundle:Content')->findOneBy(array(
            'contentType' => 'welcome',
        ));

        $timeExecute = microtime(true) - $start;

        $collectiveChains = $em->getRepository('ThoughtBundle:Chain')->
        findBy([
            'isCollective'  => true
        ]);

        $dynamicBanners = $em->getRepository(Banner::class)->findAll();

        $response =  $this->render('ThoughtBundle::homepage.html.twig', [
            'thoughts'    => $pagination,
            'comments'    => $comments,
            'timeExecute' => $timeExecute,
            'welcomeText' => $welcomeText,
            'cloud'       => $cloud['cloud'],
            'cloudStyle'  => $cloud['cloudStyle'],
            'filtersOpen' => isset($search['filter_open']) ? $search['filter_open'] : false,
            'colChains'   => $collectiveChains,
            'banners'     => $dynamicBanners
        ]);

        if (!$request->cookies->get('modal')) {
            $time = time() + (3600 * 24 * 7);
            $response->headers->setCookie(new Cookie('modal', true, $time));
        }

        return $response;
    }

    public function bannerAction(Banner $banner)
    {
        return $this->render('@Thought/include/banner.html.twig', [
            'banner' => $banner
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
     * @throws \Doctrine\ORM\OptimisticLockException
     *
     * @Route("/thought-likes/{thoughtId}", name="thought-like", requirements={"offerId" = "\d+"}, options={"expose"=true})
     */
    public function likeAction($thoughtId, Request $request)
    {
        $em = $this->getDoctrine()->getManager();

        $modelThought = $this->container->get('thought.model.thought_model');
        $recommendedThoughtService = $this->container->get('thought.recommended_thought');

        $thought = $em->getRepository('ThoughtBundle:Thought')->find($thoughtId);

        $result = 'add';

        if (!$thought) {
            return new JsonResponse(array(
                'success' => false,
                'message' => 'Quote not found',
            ));
        }
        /** @var Like[] $likes */
        $likes = $thought->getLikes();

        if (isset($likes)) {
            foreach ($likes as $like) {
                if ($like->getUser() === $this->getUser()) {
                    $ourLike = $like;
                }
            }
        }


        if (isset($ourLike)) {
            $thought = $modelThought->removeLike($thought, $this->getUser());
            $result  = 'remove';
        } else {
            $thought = $modelThought->addLike($thought, $this->getUser());
            $recommendedThoughtService->addWatchedThought($this->getUser(), $thought);
        }

        $response = new JsonResponse(array(
            'result' => $result,
            'count'  => count($thought->getLikes()),
        ));

//        $response->headers->setCookie(new Cookie('quotes', implode(',', $cookieQuotes), time() + (3600 * 48)));

        return $response;
    }
}
