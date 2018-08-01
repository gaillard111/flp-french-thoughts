<?php

namespace ThoughtBundle\Controller;

use FOS\ElasticaBundle\Elastica\Index;
use FOS\ElasticaBundle\Finder\FinderInterface;
use FOS\ElasticaBundle\Finder\TransformedFinder;
use FOS\ElasticaBundle\Paginator\PaginatorAdapterInterface;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\Route;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use ThoughtBundle\Model\AuthorModel;

/**
 * Class AuthorController
 * @package ThoughtBundle\Controller
 */
class AuthorController extends Controller
{
    /**
     * @Route("/authors-list", methods={"GET"}, options={"sitemap" = true})
     *
     * @param Request $request
     * @return Response
     */
    public function indexAction(Request $request)
    {
        $start = microtime(true);

        $page = $request->query->getInt('page', 1);

        $alpha = $request->query->getAlpha('alpha', 1);

        $countItem = 30;

        /** @var TransformedFinder $authorsFinder */
        $authorsFinder = $this->container->get('fos_elastica.finder.app.author');

        $paginator  = $this->get('knp_paginator');


        if (!$alpha) {
            $alpha = 'A';
        }

        /** @var AuthorModel $authorModel */
        $authorModel = $this->container->get('thought.model.author_model');

        $authors = $authorModel->getAuthorsByStringStartElastic($alpha, $authorsFinder);

        $pagination = $paginator->paginate(
            $authors,
            $page,
            $countItem
        );

        $timeExecute = microtime(true) - $start;

        return $this->render('ThoughtBundle::author.html.twig', array(
            'authors'     => $pagination,
            'timeExecute' => $timeExecute,
        ));
    }
}
