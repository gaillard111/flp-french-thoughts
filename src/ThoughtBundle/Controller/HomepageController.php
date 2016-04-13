<?php

namespace ThoughtBundle\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\Route;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;

/**
 * Class HomepageController
 * @package ThoughtBundle\Controller
 */
class HomepageController extends Controller
{
    /**
     * @Route("/")
     *
     * @param Request $request
     * @return Response
     */
    public function indexAction(Request $request)
    {
        $start = microtime(true);

        $modelThought = $this->container->get('thought.model.thought_model');

        $finder = $this->container->get('fos_elastica.finder.app.thought');

        $thoughts = $modelThought->getThoughtsFromElastic($request->get('search'), $finder);

        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $thoughts,
            $request->query->getInt('page', 1),
            10
        );

        $timeExecute = microtime(true) - $start;

        return $this->render('ThoughtBundle::homepage.html.twig', array(
            'thoughts'    => $pagination,
            'timeExecute' => $timeExecute,
        ));
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
}
